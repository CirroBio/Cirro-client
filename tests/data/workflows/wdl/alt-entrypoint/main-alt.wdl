version 1.1

workflow main_alt {
    input {
        String alt_required_string
        Boolean alt_required_bool
        Int alt_required_int
        Float alt_required_float
        File alt_required_path

        String? alt_optional_string = 'optional'
        Boolean? alt_optional_bool = false
        Int? alt_optional_int = 42
        Float? alt_optional_float = 3.14
        File? alt_optional_path = "/dev/null"
    }

    call foo {
        input:
            required_string=alt_required_string
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