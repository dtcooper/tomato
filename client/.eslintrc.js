module.exports = {
  env: {
    browser: true,
    es2021: true
  },
  extends: ["eslint:recommended", "plugin:svelte/recommended"],
  globals: {
    TOMATO_VERSION: true
  },
  overrides: [
    {
      env: {
        node: true
      },
      files: [".eslintrc.{js,cjs}", "src/main*.js"],
      parserOptions: {
        sourceType: "script"
      },
      globals: {
        TOMATO_VERSION: true,
      },
    }
  ],
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module"
  },
  rules: {}
}
