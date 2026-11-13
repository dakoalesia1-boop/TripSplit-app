CREATE TABLE groups (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(255) NOT NULL
);

CREATE TABLE participants (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(255) NOT NULL,
    group_id INT NOT NULL,
    FOREIGN KEY (group_id) REFERENCES groups(id)
);

CREATE TABLE expenses (
    id INT IDENTITY(1,1) PRIMARY KEY,
    description NVARCHAR(255) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    category NVARCHAR(100) NOT NULL DEFAULT 'General',
    paid_by_id INT NOT NULL,
    group_id INT NOT NULL,
    FOREIGN KEY (paid_by_id) REFERENCES participants(id),
    FOREIGN KEY (group_id) REFERENCES groups(id)
);

CREATE TABLE expense_shares (
    id INT IDENTITY(1,1) PRIMARY KEY,
    expense_id INT NOT NULL,
    participant_id INT NOT NULL,
    FOREIGN KEY (expense_id) REFERENCES expenses(id),
    FOREIGN KEY (participant_id) REFERENCES participants(id)
);