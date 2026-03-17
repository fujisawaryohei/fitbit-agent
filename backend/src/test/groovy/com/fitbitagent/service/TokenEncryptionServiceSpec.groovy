package com.fitbitagent.service

import spock.lang.Specification
import spock.lang.Subject

import java.util.Base64

class TokenEncryptionServiceSpec extends Specification {

    // 256-bit (32-byte) AES key encoded as Base64 for testing
    static final String TEST_KEY = Base64.getEncoder().encodeToString(new byte[32])

    @Subject
    TokenEncryptionService service = new TokenEncryptionService(TEST_KEY)

    def "encrypt should return a non-null, non-empty Base64 string"() {
        given:
        def plainText = "my-secret-access-token"

        when:
        def result = service.encrypt(plainText)

        then:
        result != null
        !result.isEmpty()
        // Should be valid Base64
        Base64.getDecoder().decode(result) != null
    }

    def "encrypt should produce different ciphertext each time (IV is randomized)"() {
        given:
        def plainText = "my-secret-access-token"

        when:
        def first  = service.encrypt(plainText)
        def second = service.encrypt(plainText)

        then:
        first != second
    }

    def "decrypt should recover the original plain text"() {
        given:
        def plainText = "my-secret-access-token"

        when:
        def encrypted = service.encrypt(plainText)
        def decrypted = service.decrypt(encrypted)

        then:
        decrypted == plainText
    }

    def "encrypt and decrypt are inverse operations for various inputs"() {
        when:
        def decrypted = service.decrypt(service.encrypt(input))

        then:
        decrypted == input

        where:
        input << [
            "short",
            "a" * 1000,
            "日本語のトークン",
            "token-with-special-chars !@#\$%^&*()",
        ]
    }

    def "decrypt with tampered ciphertext should throw RuntimeException"() {
        given:
        def encrypted = service.encrypt("original")
        def tampered  = encrypted + "AAAA"

        when:
        service.decrypt(tampered)

        then:
        thrown(RuntimeException)
    }

    def "TokenEncryptionService constructor should throw when key is invalid Base64"() {
        when:
        new TokenEncryptionService("not-valid-base64!!!")

        then:
        thrown(Exception)
    }
}
