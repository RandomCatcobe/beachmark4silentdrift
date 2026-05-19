# js_toy_drift

Offline JS toy drift candidate for `toy-drift.value`.

The same public JavaScript client calls:

```javascript
const toy = require("toy-drift");
console.log(toy.value());
```

Package roots:

- `old/toy-drift/index.js` returns `old`
- `new/toy-drift/index.js` returns `new`

The JS adapter runs each side with `NODE_PATH` pointing at the selected local
package root. This case is deterministic: no network, clock, randomness, or
filesystem input is used by the client.
