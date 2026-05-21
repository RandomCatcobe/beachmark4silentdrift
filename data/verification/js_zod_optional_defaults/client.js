const { z } = require("zod");

const schema = z.object({
  a: z.string().default("tuna").optional(),
});

const parsed = schema.parse({});
console.log(JSON.stringify({
  version: require("zod/package.json").version,
  keys: Object.keys(parsed),
  parsed,
}));
