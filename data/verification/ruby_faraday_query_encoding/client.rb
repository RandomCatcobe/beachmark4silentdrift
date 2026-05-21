require "json"
require "faraday"

result = {
  version: Faraday::VERSION,
  query: Faraday::Utils.build_query(q: "a b")
}

puts JSON.generate(result)
