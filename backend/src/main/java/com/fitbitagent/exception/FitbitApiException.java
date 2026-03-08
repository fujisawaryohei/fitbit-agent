package com.fitbitagent.exception;

public class FitbitApiException extends RuntimeException {
    public FitbitApiException(String message) {
        super(message);
    }
    public FitbitApiException(String message, Throwable cause) {
        super(message, cause);
    }
}
