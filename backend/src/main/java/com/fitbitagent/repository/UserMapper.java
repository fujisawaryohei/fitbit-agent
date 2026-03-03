package com.fitbitagent.repository;

import com.fitbitagent.domain.entity.User;
import org.apache.ibatis.annotations.Mapper;

import java.util.Optional;
import java.util.UUID;

public interface UserMapper {
    Optional<User> findbyId(UUID id);
    Optional<User> findbyFitbitUserId(UUID id);
    void insert(User user);
    void update(User user);
}