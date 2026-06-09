const swaggerJsdoc = require('swagger-jsdoc');

const options = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'Billing Service API',
      version: '1.0.0',
      description: 'API dokumentasi untuk sistem Billing/Asuransi Rumah Sakit'
    },
    servers: [
      {
        url: 'http://localhost:8003',
        description: 'Development server'
      }
    ]
  },
  apis: ['./src/routes/*.js']
};

module.exports = swaggerJsdoc(options);