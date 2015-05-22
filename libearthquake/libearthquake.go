// Copyright (C) 2015 Nippon Telegraph and Telephone Corporation.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
// implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package main

import (
	"C"
	. "./equtils"
	"encoding/json"	
)

type libExecution struct {
	searchDir string
}

var (
	libExe *libExecution
)

//export EQInitCtx
func EQInitCtx(configJsonCString *C.char) bool {
	configJson := C.GoString(configJsonCString)
	jsonBuf := []byte(configJson)
	libExe := &libExecution{}
	var root map[string]interface{}
	err := json.Unmarshal(jsonBuf, &root)
	if err != nil {
		Log("unmarsharing execution file: %s failed (%s)", configJson, err)
		return false
	}
	globalFlags := root["globalFlags"].(map[string]interface{})
	// direct := int(globalFlags["direct"].(float64))
	// if direct > 0 {
	// 	Log("WARN: direct mode is deprecated, because you can use socat to connect between inside the VM and outside the VM")
	// }
	ocFlags := globalFlags["orchestrator"].(map[string]interface{})
	searchFlags := ocFlags["search"].(map[string]interface{})
	searchDir := searchFlags["directory"].(string)
	Log("searchDir: %s", searchDir)
	libExe.searchDir = searchDir
	return true
}

//TODO: implement historystorage library

//export EQFreeCtx
func EQFreeCtx() bool {
	return true
}


func main() {
	Log("this dummy main() is required: http://qiita.com/yanolab/items/1e0dd7fd27f19f697285")
}
