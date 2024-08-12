module.exports = {
  env: {
    browser: true,
    es2021: true
    //node: true
  },
  extends: ["eslint:recommended", "plugin:svelte/recommended"],
  globals: {
    IS_LINUX: true,
    IS_MAC: true,
    IS_WIN32: true,
    TOMATO_VERSION: true
  },
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
      globals: {
        IS_LINUX: true,
        IS_MAC: true,
        IS_WIN32: true,
        TOMATO_VERSION: true
      }
    }
  ],
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module"
  }
}
