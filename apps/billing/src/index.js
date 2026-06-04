require('dotenv').config();
const express = require('express');
const mongoose = require('mongoose');
const startConsumer = require('./consumers/patientConsumer');
const invoiceRoutes = require('./routes/invoiceRoutes');

const app = express();
app.use(express.json());

const PORT = process.env.PORT || 8003;

mongoose.connect(process.env.MONGODB_URI)
  .then(() => {
    console.log('Connected to MongoDB');
    startConsumer();
  })
  .catch((err) => console.error('MongoDB connection error:', err));

app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'billing' });
});

app.use('/api/v1/invoices', invoiceRoutes);

app.listen(PORT, () => {
  console.log(`Billing service running on port ${PORT}`);
});