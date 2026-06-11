const amqp = require('amqplib');
const Invoice = require('../models/Invoice');

async function startConsumer() {
  try {
    const connection = await amqp.connect(process.env.RABBITMQ_URL);
    const channel = await connection.createChannel();

    const exchange = 'hospital.events';
    const queue = 'billing.patient.registered';
    const routingKey = 'patient.registered';

    await channel.assertExchange(exchange, 'topic', { durable: true });
    await channel.assertQueue(queue, { durable: true });
    await channel.bindQueue(queue, exchange, routingKey);

    console.log('Waiting for patient.registered events...');

    channel.consume(queue, async (msg) => {
      if (msg) {
        try {
          const event = JSON.parse(msg.content.toString());
          const { patient_id, full_name, registration_type } = event.data;

          const existing = await Invoice.findOne({ patient_id });
          if (!existing) {
            await Invoice.create({
              patient_id,
              full_name,
              registration_type,
              items: [],
              total: 0,
              status: 'UNPAID'
            });
            console.log(`Invoice created for patient: ${full_name}`);
          }

          channel.ack(msg);
        } catch (error) {
          console.error('Error processing message, dropping it:', error.message);
          channel.ack(msg); // Ack to prevent poison message loop
        }
      }
    });

  } catch (err) {
    console.error('Consumer error:', err);
    setTimeout(startConsumer, 5000);
  }
}

module.exports = startConsumer;