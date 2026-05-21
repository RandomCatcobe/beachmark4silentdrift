require "json"
require "rack"

input = "a=1;b=2&c=3"
parsed = Rack::Utils.parse_nested_query(input)

puts JSON.generate({
  version: Rack.release,
  input: input,
  parsed: parsed
})
