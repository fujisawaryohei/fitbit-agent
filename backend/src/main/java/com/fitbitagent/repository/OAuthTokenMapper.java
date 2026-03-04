package com.fitbitagent.repository;

import com.fitbitagent.domain.entity.OAuthToken;
import org.apache.ibatis.annotations.Mapper;

import java.util.Optional;
import java.util.UUID;

@Mapper
public interface OAuthTokenMapper {
    Optional<OAuthToken> findByUserId(UUID userId);
    void insert(OAuthToken oAuthToken);
    void update(OAuthToken oAuthToken);
}
