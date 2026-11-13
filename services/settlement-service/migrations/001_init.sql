CREATE TABLE settlements (
    id INT IDENTITY(1,1) PRIMARY KEY,
    payer_id INT NOT NULL,
    receiver_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    group_id INT NOT NULL
);