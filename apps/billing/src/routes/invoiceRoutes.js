const express = require('express');
const router = express.Router();
const Invoice = require('../models/Invoice');
const publishInvoiceCreated = require('../publishers/invoicePublisher');

// Lihat semua tagihan
router.get('/', async (req, res) => {
  try {
    const invoices = await Invoice.find();
    res.json(invoices);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Lihat tagihan berdasarkan patient_id
router.get('/:patient_id', async (req, res) => {
  try {
    const invoice = await Invoice.findOne({ patient_id: req.params.patient_id });
    if (!invoice) return res.status(404).json({ error: 'Invoice not found' });
    res.json(invoice);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Update status tagihan menjadi PAID
router.patch('/:patient_id/pay', async (req, res) => {
  try {
    const invoice = await Invoice.findOneAndUpdate(
      { patient_id: req.params.patient_id },
      { status: 'PAID' },
      { new: true }
    );
    if (!invoice) return res.status(404).json({ error: 'Invoice not found' });

    // Kirim event invoice.created dalam format XML ke RabbitMQ
    await publishInvoiceCreated(invoice);

    res.json(invoice);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;