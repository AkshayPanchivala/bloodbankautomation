const path = require('path');
require("dotenv").config({ path: path.join(__dirname, '.env') });
const mongoose = require('mongoose');
const app = require('./app');
const AppError = require('./Utils/appError');

const connection = async () => {
    try {
        if (!process.env.database_url) {
            console.error("Database connection error: 'database_url' is not defined in backend/.env");
            return;
        }
        const DB = await mongoose.connect(process.env.database_url);
        console.log("Successfully connected your application with database!!");
    } catch (err) {
        console.error("Database connection refused:", err.message);
    }
};

connection();

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
