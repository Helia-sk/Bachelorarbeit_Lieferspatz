-- Insert sample restaurants (all with password '1')
INSERT INTO restaurants (username, name, street, postal_code, description, image_url, password_hash, balance)
VALUES
  ('pizza_palace', 'Pizza Palace', 'Main Street 1', '47057', 'Best pizza in town!', 'https://example.com/pizza.jpg', '1', 0.00),
  ('sushi_world', 'Sushi World', 'Ocean Avenue 5', '47057', 'Fresh sushi and more.', 'https://example.com/sushi.jpg', '1', 0.00),
  ('burger_hub', 'Burger Hub', 'Burger Lane 10', '47057', 'Juicy burgers and fries.', 'https://example.com/burger.jpg', '1', 0.00);

-- Insert opening hours for each restaurant (open on Sunday only, day_of_week=0)
INSERT INTO opening_hours (restaurant_id, day_of_week, open_time, close_time)
VALUES
  (6, 0, '11:00', '22:00'),
  (7, 0, '12:00', '21:00'),
  (8, 0, '10:00', '23:00');

-- Insert delivery areas for each restaurant (all 47057)
INSERT INTO delivery_areas (restaurant_id, postal_code)
VALUES
  (6, '47057'),
  (7, '47057'),
  (8, '47057');

-- Insert menu items for restaurants with id 6, 7, 8
INSERT INTO menu_items (restaurant_id, name, description, price, image_url, is_available, category)
VALUES
  -- For restaurant 6
  (6, 'Margherita Pizza', 'Classic pizza with tomato sauce and mozzarella', 8.50, 'https://example.com/margherita.jpg', 1, 'Pizza'),
  (6, 'Pepperoni Pizza', 'Spicy pepperoni and cheese', 9.50, 'https://example.com/pepperoni.jpg', 1, 'Pizza'),
  -- For restaurant 7
  (7, 'Salmon Sushi', 'Fresh salmon on rice', 12.00, 'https://example.com/salmon_sushi.jpg', 1, 'Sushi'),
  (7, 'Avocado Maki', 'Avocado roll with seaweed', 7.00, 'https://example.com/avocado_maki.jpg', 1, 'Sushi'),
  -- For restaurant 8
  (8, 'Classic Burger', 'Beef patty, lettuce, tomato, cheese', 10.00, 'https://example.com/classic_burger.jpg', 1, 'Burger'),
  (8, 'Veggie Burger', 'Vegetarian patty with fresh veggies', 9.00, 'https://example.com/veggie_burger.jpg', 1, 'Burger');
