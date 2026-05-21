const dotenv = require("dotenv");

const source = "SECRET=abc#def\nQUOTED=\"abc#def\"\n";
const parsed = dotenv.parse(source);

console.log(JSON.stringify({
  version: require("dotenv/package.json").version,
  parsed,
}));
