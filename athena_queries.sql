-- 1. Count total asteroids
SELECT COUNT(*) AS total_asteroids
FROM asteroids;
-- 2. Count potentially hazardous asteroids
SELECT COUNT(*) AS hazardous_asteroids
FROM asteroids
WHERE hazardous = true;
-- 3. Find the 10 closest asteroids
SELECT
    id,
    name,
    miss_distance_km
FROM asteroids
ORDER BY miss_distance_km ASC
LIMIT 10;
-- 4. Calculate average miss distance
SELECT
    AVG(miss_distance_km) AS average_miss_distance_km
FROM asteroids;
-- 5. Count asteroids by hazardous status
SELECT
    hazardous,
    COUNT(*) AS asteroid_count
FROM asteroids
GROUP BY hazardous;
-- 6. Find the 10 closest potentially hazardous asteroids
SELECT
    id,
    name,
    miss_distance_km
FROM asteroids
WHERE hazardous = true
ORDER BY miss_distance_km ASC
LIMIT 10;
-- 7. Count asteroid approaches by date
SELECT
    closest_approach_date,
    COUNT(*) AS asteroid_count
FROM asteroids
GROUP BY closest_approach_date
ORDER BY closest_approach_date;
-- 8. Find the 10 farthest asteroids
SELECT
    id,
    name,
    miss_distance_km
FROM asteroids
ORDER BY miss_distance_km DESC
LIMIT 10;
-- 9. Find the single closest asteroid
SELECT
    id,
    name,
    closest_approach_date,
    miss_distance_km,
    hazardous
FROM asteroids
ORDER BY miss_distance_km ASC
LIMIT 1;
-- 10. Find potentially hazardous asteroids more than 10 million km away
SELECT
    id,
    name,
    miss_distance_km
FROM asteroids
WHERE hazardous = true
  AND miss_distance_km > 10000000
ORDER BY miss_distance_km ASC;