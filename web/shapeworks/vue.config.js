const vtkChainWebpack = require('vtk.js/Utilities/config/chainWebpack');

module.exports = {
  devServer: {
    overlay: {
      warnings: false,
      errors: false,
    },
  },
  chainWebpack: (config) => {
    vtkChainWebpack(config);
  }
}
