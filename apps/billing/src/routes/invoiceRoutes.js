const express = require('express');
const router = express.Router();
const Invoice = require('../models/Invoice');
const publishInvoiceCreated = require('../publishers/invoicePublisher');

/**
 * @swagger
 * components:
 *   schemas:
 *     InvoiceItem:
 *       type: object
 *       properties:
 *         description:
 *           type: string
 *           example: Resep RES-20240601-ABC123
 *         amount:
 *           type: number
 *           example: 150000
 *     Invoice:
 *       type: object
 *       properties:
 *         patient_id:
 *           type: string
 *           example: REG-001
 *         full_name:
 *           type: string
 *           example: Budi Santoso
 *         registration_type:
 *           type: string
 *           enum: [UMUM, BPJS]
 *           example: UMUM
 *         items:
 *           type: array
 *           items:
 *             $ref: '#/components/schemas/InvoiceItem'
 *         total:
 *           type: number
 *           example: 150000
 *         status:
 *           type: string
 *           enum: [UNPAID, PAID]
 *           example: UNPAID
 *         created_at:
 *           type: string
 *           format: date-time
 */

/**
 * @swagger
 * /api/v1/invoices:
 *   get:
 *     summary: Lihat semua tagihan
 *     tags: [Invoices]
 *     responses:
 *       200:
 *         description: Daftar semua tagihan
 *         content:
 *           application/json:
 *             schema:
 *               type: array
 *               items:
 *                 $ref: '#/components/schemas/Invoice'
 */
router.get('/', async (req, res) => {
  try {
    const invoices = await Invoice.find();
    res.json(invoices);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

/**
 * @swagger
 * /api/v1/invoices/{patient_id}:
 *   get:
 *     summary: Lihat tagihan berdasarkan patient_id
 *     tags: [Invoices]
 *     parameters:
 *       - in: path
 *         name: patient_id
 *         required: true
 *         schema:
 *           type: string
 *         example: REG-001
 *     responses:
 *       200:
 *         description: Data tagihan pasien
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Invoice'
 *       404:
 *         description: Tagihan tidak ditemukan
 */
router.get('/:patient_id', async (req, res) => {
  try {
    const invoice = await Invoice.findOne({ patient_id: req.params.patient_id });
    if (!invoice) return res.status(404).json({ error: 'Invoice not found' });
    res.json(invoice);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

/**
 * @swagger
 * /api/v1/invoices/{patient_id}/pay:
 *   patch:
 *     summary: Update status tagihan menjadi PAID
 *     tags: [Invoices]
 *     parameters:
 *       - in: path
 *         name: patient_id
 *         required: true
 *         schema:
 *           type: string
 *         example: REG-001
 *     responses:
 *       200:
 *         description: Tagihan berhasil diupdate, event XML dikirim ke RabbitMQ
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/Invoice'
 *       404:
 *         description: Tagihan tidak ditemukan
 */
router.patch('/:patient_id/pay', async (req, res) => {
  try {
    const invoice = await Invoice.findOneAndUpdate(
      { patient_id: req.params.patient_id },
      { status: 'PAID' },
      { new: true }
    );
    if (!invoice) return res.status(404).json({ error: 'Invoice not found' });

    await publishInvoiceCreated(invoice);

    res.json(invoice);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;