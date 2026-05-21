test('snapshot shape', () => {
  expect({ text: 'line\nbreak', nested: { value: 1 } }).toMatchSnapshot();
});
