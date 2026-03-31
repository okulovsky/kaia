# Kaia-client-scripts

This is a set of typescript/javascript helpers to build an integration with https://github.com/okulovsky/kaia

They are initially created by https://github.com/okulovsky and are designed to help engineers create their own frontend for Kaia.

Example of frontend project, using these scripts can be found in `../web-client` folder 

## Usage

You can use scripts from this folder just by simply importing them in your TS project:

1. import ... from `web-scripts`

You can also build the project and use it as npm pack

1. Run `deploy.py` -- get `.zip` archive with library
2. Link this archive in package.json `dependencies:<link-to-zip>`
3. Import like usual

You can also build the project and deploy it to npm -- see `deploy.py` for reference. 

## Development

### Lint code and fix errros:

`npm run lint:fix`