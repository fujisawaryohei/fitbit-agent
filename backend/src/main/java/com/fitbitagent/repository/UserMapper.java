package com.fitbitagent.repository;

import com.fitbitagent.domain.entity.User;
import org.apache.ibatis.annotations.Mapper;

import java.util.Optional;
import java.util.UUID;

@Mapper
public interface UserMapper {
    Optional<User> findById(UUID id);
    Optional<User> findByFitbitUserId(String fitbitUserId);
    void insert(User user);
    void update(User user);
}