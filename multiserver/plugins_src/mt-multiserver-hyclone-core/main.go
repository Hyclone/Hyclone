package main

import (
	"fmt"
)

func init() {
	fmt.Println("Hello!")
	/*http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintf(w, fmt.Sprint(proxy.Players()))
    })*/
    //http.ListenAndServe(":5050", nil)
}