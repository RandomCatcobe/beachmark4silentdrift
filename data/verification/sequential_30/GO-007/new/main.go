package main

import (
	"fmt"

	yaml "gopkg.in/yaml.v3"
)

func main() {
	var v map[string]any
	if err := yaml.Unmarshal([]byte("flag: on\nnope: no\n"), &v); err != nil {
		panic(err)
	}
	fmt.Printf("flag=%T:%v nope=%T:%v\n", v["flag"], v["flag"], v["nope"], v["nope"])
}
