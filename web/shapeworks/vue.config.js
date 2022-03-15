const path = require('path');
const CopyPlugin = require('copy-webpack-plugin');
const vtkChainWebpack = require('vtk.js/Utilities/config/chainWebpack');

module.exports = {
  devServer: {
    overlay: {
      warnings: false,
      errors: false,
    },
  },
  configureWebpack: {
    plugins: [
      new CopyPlugin([
        {
          from: path.join(__dirname, 'node_modules', 'itk'),
          to: 'itk',
        },
      ]),
    ],
  },
  chainWebpack: (config) => {
    vtkChainWebpack(config);
  }
}
