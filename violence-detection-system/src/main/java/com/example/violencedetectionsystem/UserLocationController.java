package com.example.violencedetectionsystem;
import org.springframework.web.bind.annotation.*;
import org.springframework.beans.factory.annotation.Autowired;

import java.util.List;

@RestController
@RequestMapping("/location")
public class UserLocationController {

    @Autowired
    private UserLocationRepository repository;

    @PostMapping("/save")
    public UserLocation save(
            @RequestBody UserLocation location) {

        return repository.save(location);
    }
    @GetMapping("/nearby")
    public List<UserLocation> nearby(
            @RequestParam double lat,
            @RequestParam double lon) {

        List<UserLocation> all =
                repository.findAll();

        return all.stream()
                .filter(location ->
                        DistanceUtil.distance(
                                lat,
                                lon,
                                location.getLatitude(),
                                location.getLongitude()
                        ) <= 5
                )
                .toList();
    }
}
