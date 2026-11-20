UPDATE expenses
SET category = CASE
    WHEN category IS NULL OR LTRIM(RTRIM(category)) = ''
        THEN 'General'
    ELSE LTRIM(RTRIM(category))
END
WHERE category IS NULL
   OR LTRIM(RTRIM(category)) = ''
   OR category <> LTRIM(RTRIM(category));
