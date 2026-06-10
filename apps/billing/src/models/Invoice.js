const mongoose = require('mongoose');

const invoiceItemSchema = new mongoose.Schema({
  description: String,
  amount: Number
});

const invoiceSchema = new mongoose.Schema({
  patient_id: { type: String, required: true },
  full_name: { type: String, required: true },
  registration_type: { type: String, enum: ['UMUM', 'BPJS'] },
  items: [invoiceItemSchema],
  total: { type: Number, default: 0 },
  status: { type: String, enum: ['UNPAID', 'PAID'], default: 'UNPAID' },
  created_at: { type: Date, default: Date.now }
});

module.exports = mongoose.model('Invoice', invoiceSchema);