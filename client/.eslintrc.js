const globals = {
  BUILD_YEAR: true,
  BUILD_DATETIME: true,
  IS_LINUX: true,
  IS_MAC: true,
  IS_WIN32: true,
  TOMATO_VERSION: true
}

module.exports = {
  env: {
    browser: true,
    es2021: true
    //node: true
  },
  extends: ["eslint:recommended", "plugin:svelte/recommended"],
  globals,
  rules: {
    "svelte/no-at-html-tags": "off"
  },
  overrides: [
    {
      env: {
        node: true
      },
      files: [".eslintrc.{js,cjs}", "src/main*.js", "scripts/**/*"],
      parserOptions: {
        sourceType: "script"
      },
      globals
    }
  ],
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module"
  }
}
