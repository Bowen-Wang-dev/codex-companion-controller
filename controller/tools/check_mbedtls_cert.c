/* Host-only regression probe. Link to the same Mbed TLS source version as IDF.
 * Does not open sockets or perform model/account operations. */
#include "mbedtls/x509_crt.h"
#include "mbedtls/error.h"
#include <stdio.h>

int main(int argc, char **argv) {
    if (argc != 3) {
        fprintf(stderr, "usage: check_mbedtls_cert CERT.pem HOST_OR_IP\n");
        return 2;
    }
    mbedtls_x509_crt certificate;
    mbedtls_x509_crt_init(&certificate);
    int result = mbedtls_x509_crt_parse_file(&certificate, argv[1]);
    if (result != 0) {
        char message[160];
        mbedtls_strerror(result, message, sizeof(message));
        printf("parse: -0x%04x %s\n", -result, message);
    } else {
        unsigned int flags = 0;
        result = mbedtls_x509_crt_verify(&certificate, &certificate, NULL,
                                        argv[2], &flags, NULL, NULL);
        printf("parse: OK; verify: %d; flags: 0x%08x\n", result, flags);
    }
    mbedtls_x509_crt_free(&certificate);
    return result != 0;
}
