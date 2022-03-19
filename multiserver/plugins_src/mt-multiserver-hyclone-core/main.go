package main

import (
	"log"
)

func init() {
	log.Println("[mt-multiserver-hyclone-core] Hello!")
	/*http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintf(w, fmt.Sprint(proxy.Players()))
    })*/
    //http.ListenAndServe(":5050", nil)
}