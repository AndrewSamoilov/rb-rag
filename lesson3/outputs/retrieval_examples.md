Query: How do I skip logging?
================================================================================
#1 | distance=0.5401 | doc_chunk_038
### Skip logging...
--------------------------------------------------------------------------------
#2 | distance=0.8925 | doc_chunk_039
  ```go func main() {   router := gin.New()    // skip logging for desired paths by setting SkipPaths in LoggerConfig   loggerConfig := gin.LoggerConfig{SkipPaths: []string{"/metrics"}}    // skip logging based on your log...
--------------------------------------------------------------------------------
#3 | distance=1.1169 | doc_chunk_034
  ## Logging  > Control log output, formatting, and filtering.  ### How to write log file  ```go func main() {   // Disable Console Color, you don't need console color when writing the logs to file.   gin.DisableConsoleCol...
--------------------------------------------------------------------------------
Comment: partially relevant

Query: How do I define a GET route in Gin?
#1 | distance=0.8076 | README_chunk_008
  **Running the application:**  1. Save the code above as `main.go` 2. Run the application:     ```sh    go run main.go    ```  3. Open your browser and visit [`http://localhost:8080/ping`](http://localhost:8080/ping) 4. Y...
--------------------------------------------------------------------------------
#2 | distance=0.8866 | doc_chunk_066
  ### Bind Uri  See the [detail information](https://github.com/gin-gonic/gin/issues/846).  ```go package main  import (   "net/http"    "github.com/gin-gonic/gin" )  type Person struct {   ID string `uri:"id" binding:"req...
--------------------------------------------------------------------------------
#3 | distance=0.8900 | doc_chunk_030
  ```go // simulate some private data var secrets = gin.H{   "foo":    gin.H{"email": "foo@bar.com", "phone": "123433"},   "austin": gin.H{"email": "austin@example.com", "phone": "666"},   "lena":   gin.H{"email": "lena@gu...
--------------------------------------------------------------------------------
Comment: partially relevant


Query: How to do a graceful shutdown?
#1 | distance=0.8319 | doc_chunk_117
  #### Manually  In case you are using Go 1.8 or a later version, you may not need to use those libraries. Consider using `http.Server`'s built-in [Shutdown()](https://pkg.go.dev/net/http#Server.Shutdown) method for gracef...
--------------------------------------------------------------------------------
#2 | distance=1.0351 | doc_chunk_115
  ### Graceful shutdown or restart  There are a few approaches you can use to perform a graceful shutdown or restart. You can make use of third-party packages specifically built for that, or you can manually do the same wi...
--------------------------------------------------------------------------------
#3 | distance=1.0727 | doc_chunk_116
  ```go router := gin.Default() router.GET("/", handler) // [...] endless.ListenAndServe(":4242", router) ```  Alternatives:  - [grace](https://github.com/facebookgo/grace): Graceful restart & zero downtime deploy for Go s...
--------------------------------------------------------------------------------
Comment: relevant


Query: router GET POST example
================================================================================
#1 | distance=1.0810 | doc_chunk_016
  ```sh POST /post?id=1234&page=1 HTTP/1.1 Content-Type: application/x-www-form-urlencoded  name=manu&message=this_is_great ```  ```go func main() {   router := gin.Default()    router.POST("/post", func(c *gin.Context) { ...
--------------------------------------------------------------------------------
#2 | distance=1.0840 | doc_chunk_015
  ### Multipart/Urlencoded Form  ```go func main() {   router := gin.Default()    router.POST("/form_post", func(c *gin.Context) {     message := c.PostForm("message")     nick := c.DefaultPostForm("nick", "anonymous")    ...
--------------------------------------------------------------------------------
#3 | distance=1.1020 | doc_chunk_017
  ```sh id: 1234; page: 1; name: manu; message: this_is_great ```  ### Map as querystring or postform parameters  ```sh POST /post?ids[a]=1234&ids[b]=hello HTTP/1.1 Content-Type: application/x-www-form-urlencoded  names[fi...
Comment: relevant



 Query: explaine pls how can i do post request
================================================================================
#1 | distance=1.0435 | doc_chunk_010
  ## Routing  > Learn how to define routes, handle parameters, and organize endpoints.  ### Using GET, POST, PUT, PATCH, DELETE and OPTIONS...
--------------------------------------------------------------------------------
#2 | distance=1.1717 | doc_chunk_017
  ```sh id: 1234; page: 1; name: manu; message: this_is_great ```  ### Map as querystring or postform parameters  ```sh POST /post?ids[a]=1234&ids[b]=hello HTTP/1.1 Content-Type: application/x-www-form-urlencoded  names[fi...
--------------------------------------------------------------------------------
#3 | distance=1.1987 | doc_chunk_051
  Sample request  ```sh $ curl -v -X POST \   http://localhost:8080/loginJSON \   -H 'content-type: application/json' \   -d '{ "user": "manu" }' > POST /loginJSON HTTP/1.1 > Host: localhost:8080 > User-Agent: curl/7.51.0 ...
--------------------------------------------------------------------------------
