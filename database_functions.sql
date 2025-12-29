--  trşgger / stored procedure

CREATE OR REPLACE FUNCTION get_overdue_books()
RETURNS TABLE (
    lending_id INT,
    user_email VARCHAR,
    user_name VARCHAR,
    book_title VARCHAR,
    due_date TIMESTAMP,
    days_overdue INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        l.id,
        u.email,
        u.name,
        b.title,
        l.due_date,
        EXTRACT(DAY FROM NOW() - l.due_date)::INT
    FROM lendings l
    JOIN users u ON l.user_id = u.id
    JOIN books b ON l.book_id = b.id
    WHERE l.returned = FALSE AND l.due_date < NOW();
END;
$$ LANGUAGE plpgsql;

-- stored pr
CREATE OR REPLACE FUNCTION calculate_fine(p_lending_id INT)
RETURNS NUMERIC AS $$
DECLARE
    v_days INT;
    v_fine NUMERIC;
BEGIN
    SELECT EXTRACT(DAY FROM NOW() - due_date)::INT INTO v_days
    FROM lendings
    WHERE id = p_lending_id AND returned = FALSE AND due_date < NOW();
    
    IF v_days IS NULL OR v_days <= 0 THEN
        RETURN 0;
    END IF;
    
    v_fine := v_days * 1.0;
    RETURN v_fine;
END;
$$ LANGUAGE plpgsql;

-- trigger
CREATE OR REPLACE FUNCTION update_book_available()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.returned = TRUE AND OLD.returned = FALSE THEN
        UPDATE books SET available = available + 1 WHERE id = NEW.book_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_book_return ON lendings;
CREATE TRIGGER trg_book_return
    AFTER UPDATE ON lendings
    FOR EACH ROW
    EXECUTE FUNCTION update_book_available();

-- 2. trigger
CREATE OR REPLACE FUNCTION decrease_book_available()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE books SET available = available - 1 WHERE id = NEW.book_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_book_borrow ON lendings;
CREATE TRIGGER trg_book_borrow
    AFTER INSERT ON lendings
    FOR EACH ROW
    EXECUTE FUNCTION decrease_book_available();

-- SELECT * FROM get_overdue_books();
-- SELECT calculate_fine(1);

