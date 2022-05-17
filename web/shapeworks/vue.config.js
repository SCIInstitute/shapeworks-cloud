const path = require('path');
const CopyPlugin = require('copy-webpack-plugin');
const vtkChainWebpack = require('vtk.js/Utilities/config/chainWebpack');

module.exports = {
  devServer: {
    overlay: {
      warnings: false,
      errors: false,
    },
    progress: false,
  },
  transpileDependencies: [
    "vuetify", "@koumoul/vjsf"
  ],
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
