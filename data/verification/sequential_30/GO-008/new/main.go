package main

import (
	"bytes"
	"fmt"
	"math"

	"github.com/BurntSushi/toml"
)

func main() {
	values := map[string]any{
		"plain": 1.0,
		"nan":   math.NaN(),
		"inf":   math.Inf(1),
	}
	var buf bytes.Buffer
	if err := toml.NewEncoder(&buf).Encode(values); err != nil {
		fmt.Printf("err=%T:%v\n", err, err)
		return
	}
	fmt.Print(buf.String())
}
