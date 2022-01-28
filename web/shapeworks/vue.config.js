module.exports = {
  devServer: {
    overlay: {
      warnings: false,
      errors: false,
    },
    disableHostCheck: true,
  },
  chainWebpack: (config) => {
    // Add vtk.js shader loader
    config.module
      .rule('glsl')
      .test(/\.glsl$/)
      .use('shader-loader')
      .loader('shader-loader');

    // Add vtk.js worker loader
    config.module
      .rule('worker')
      .test(/\.worker\.js$/)
      .use('worker-loader')
      .loader('worker-loader')
      .options({
        inline: true,
        fallback: false,
      });

    // fix development with npm link
    config.resolve.symlinks(false);

    // Fix an issue with HMR and the worker-loader
    // https://github.com/webpack/webpack/issues/6642
    // https://github.com/vuejs/vue-cli/issues/2276
    if (process.env.NODE_ENV !== 'production') {
      config.output.globalObject('this');
    }
  },
  transpileDependencies: [
    'vuetify'
  ],
  // in Django's TEMPLATE_DIRS
  outputDir: '../../shapeworks_cloud/staticfiles',
  // Django's STATIC_URL
  assetsDir: '.',
}
