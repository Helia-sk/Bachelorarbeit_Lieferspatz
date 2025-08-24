import initSqlJs, { Database } from 'sql.js';
import initSQL from '../db/init.sql?raw';
import seedSQL from '../db/seed.sql?raw';

let db: Database | null = null;

export const initDB = async () => {
  if (db) return db;
  
  try {
    const SQL = await initSqlJs({
      // Use local WASM file that matches the installed sql.js version
      locateFile: file => `/node_modules/sql.js/dist/${file}`
    });
    
    db = new SQL.Database();
    
    try {
      // Initialize schema
      db.run(initSQL);
      
      // Seed data
      db.run(seedSQL);
      
      console.log('Database initialized successfully');
      return db;
    } catch (error) {
      console.error('Failed to execute SQL:', error);
      throw error;
    }
  } catch (error) {
    console.error('Failed to initialize SQL.js:', error);
    throw new Error('Database initialization failed. Please try again later.');
  }
};

export const getDB = () => {
  if (!db) throw new Error('Database not initialized');
  return db;
};

export const executeQuery = (sql: string, params: any[] = []) => {
  const db = getDB();
  try {
    const stmt = db.prepare(sql);
    stmt.bind(params);
    const result = [];
    while (stmt.step()) {
      result.push(stmt.getAsObject());
    }
    stmt.free();
    return result;
  } catch (error) {
    console.error('Error executing query:', sql, error);
    throw error;
  }
};