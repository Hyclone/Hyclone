package main

import (
	"fmt"
	"net/http"

	proxy "github.com/HimbeerserverDE/mt-multiserver-proxy"
)

func init() {
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintf(w, fmt.Sprint(proxy.Players()))
    })
    http.ListenAndServe(":5050", nil)
}


