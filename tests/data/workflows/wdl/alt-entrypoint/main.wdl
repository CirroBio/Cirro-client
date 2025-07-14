version 1.1

workflow main {
    input {
        String required_string
        Boolean required_bool
        Int required_int
        Float required_float
        File required_path

        String? optional_string = 'optional'
        Boolean? optional_bool = false
        Int? optional_int = 42
        Float? optional_float = 3.14
        File? optional_path = "/dev/null"
    }

    call foo {
        input:
            required_string=required_string
    }
}

task foo {
    input {
        String required_string
    }
    runtime {
        cpu: 2
        memory: "2 GiB"
    }
    command <<<
        echo "~{required_string}"
    >>>
    output {
        File out = stdout()
    }
}