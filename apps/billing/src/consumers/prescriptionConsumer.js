const amqp = require('amqplib');
const Invoice = require('../models/Invoice');

async function startPrescriptionConsumer() {
  try {
    const connection = await amqp.connect(process.env.RABBITMQ_URL);
    const channel = await connection.createChannel();

    const exchange = 'hospital.events';
    const queue = 'billing.prescription.dispensed';
    const routingKey = 'prescription.dispensed';

    await channel.assertExchange(exchange, 'topic', { durable: true });
    await channel.assertQueue(queue, { durable: true });
    await channel.bindQueue(queue, exchange, routingKey);

    console.log('Waiting for prescription.dispensed events...');

    channel.consume(queue, async (msg) => {
      if (msg) {
        const event = JSON.parse(msg.content.toString());
        const { patient_id, nama_pasien, total_harga, nomor_resep } = event.data;

        // Cari invoice berdasarkan patient_id
        const invoice = await Invoice.findOne({ patient_id });

        if (invoice) {
          // Tambahkan item biaya obat ke tagihan yang sudah ada
          invoice.items.push({
            description: `Resep ${nomor_resep}`,
            amount: total_harga
          });
          invoice.total += total_harga;
          await invoice.save();
          console.log(`Invoice updated for patient: ${nama_pasien}`);
        } else {
          // Jika invoice belum ada, buat baru
          await Invoice.create({
            patient_id,
            full_name: nama_pasien,
            items: [{ description: `Resep ${nomor_resep}`, amount: total_harga }],
            total: total_harga,
            status: 'UNPAID'
          });
          console.log(`Invoice created from prescription for patient: ${nama_pasien}`);
        }

        channel.ack(msg);
      }
    });

  } catch (err) {
    console.error('Prescription consumer error:', err);
    setTimeout(startPrescriptionConsumer, 5000);
  }
}

module.exports = startPrescriptionConsumer;