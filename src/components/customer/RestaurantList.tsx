import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Clock, MapPin } from 'lucide-react';
import apiClient from '../../api';

type OpeningHour = {
  day_of_week: number;
  open_time: string;
  close_time: string;
};

type Restaurant = {
  id: number;
  name: string;
  description: string;
  street: string;
  postal_code: string;
  image_url: string;
  is_open: boolean;
  opening_hours: OpeningHour[];
};

const RestaurantList: React.FC = () => {
  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadNearbyRestaurants();
  }, []);

  const loadNearbyRestaurants = async () => {
    try {
      const response = await apiClient.get<Restaurant[]>('/api/restaurant_details/nearby', {
        withCredentials: true, // Include session cookies
      });
      console.log("loading restaurants")
      if (response.status !== 200) {
        throw new Error(`Error fetching restaurants: ${response.statusText}`);
      }

      const data: Restaurant[] = response.data;
      // Show all restaurants regardless of opening status
      setRestaurants(data);
    } catch (error) {
      console.error('Failed to load restaurants:', error);
      setError('Failed to load restaurants.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mx-auto"></div>
        <p className="text-gray-500 mt-4">Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-500">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Nearby Restaurants</h1>
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {restaurants.map((restaurant) => (
          <Link
            key={restaurant.id}
            to={`/customer/dashboard/restaurant/${restaurant.id}`}
            className="block hover:shadow-lg transition-shadow duration-200"
          >
            <div className="bg-white rounded-lg shadow overflow-hidden">
              {restaurant.image_url ? (
                <img
                  src={restaurant.image_url}
                  alt={restaurant.name}
                  className="w-full h-48 object-cover"
                />
              ) : (
                <div className="w-full h-48 bg-gray-200 flex items-center justify-center">
                  <span className="text-gray-400">No image available</span>
                </div>
              )}
              <div className="p-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  {restaurant.name}
                </h3>
                <p className="mt-1 text-sm text-gray-500">{restaurant.description}</p>
                <p className="mt-1 text-sm text-gray-500">{restaurant.street}</p>
                <div className="mt-4 flex items-center text-sm text-gray-500">
                  <MapPin className="w-4 h-4 mr-1" /> {restaurant.postal_code}
                  <Clock className="w-4 h-4 ml-4 mr-1" />
                  {restaurant.is_open ? 'Open Now' : 'Closed'}
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
};

export default RestaurantList;