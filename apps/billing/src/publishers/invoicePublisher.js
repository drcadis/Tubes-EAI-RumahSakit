const amqp = require('amqplib');
const xml2js = require('xml2js');

const builder = new xml2js.Builder({ rootName: 'event', xmldec: { version: '1.0', encoding: 'UTF-8' } });

async function publishInvoiceCreated(invoice) {
  try {
    const connection = await amqp.connect(process.env.RABBITMQ_URL);
    const channel = await connection.createChannel();

    const exchange = 'hospital.events';
    const routingKey = 'invoice.created';

    await channel.assertExchange(exchange, 'topic', { durable: true });

    // Ubah data invoice dari JSON ke XML
    const payload = {
      event_type: 'INVOICE_CREATED',
      source: 'billing-service',
      event_timestamp: new Date().toISOString(),
      data: {
        patient_id: invoice.patient_id,
        full_name: invoice.full_name,
        total: invoice.total,
        status: invoice.status
      }
    };

    const xmlPayload = builder.buildObject(payload);

    channel.publish(exchange, routingKey, Buffer.from(xmlPayload), { contentType: 'application/xml' });

    console.log(`Invoice event published as XML for patient: ${invoice.patient_id}`);
    await channel.close();
    await connection.close();

  } catch (err) {
    console.error('Publisher error:', err);
  }
}

module.exports = publishInvoiceCreated;