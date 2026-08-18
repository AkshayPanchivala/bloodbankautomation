const nodemailer = require('nodemailer')
const AppError = require('./appError')

const sendEmail = async (options) => {
	// validation of who is sending and authorization to send email
	const transporter = nodemailer.createTransport({
		service: 'gmail',
		host: process.env.EMAIL_HOST,
		port: process.env.EMAIL_PORT,
		auth: {
			user: process.env.EMAIL_USERNAME,
			pass: process.env.EMAIL_PASSWORD,
		},
	})

	// 2) defining whom to send and all other options (header, message, etc.)
	const mailOptions = {
		from: process.env.EMAIL_USERNAME,
		to: options.email,
		subject: options.subject,
		text: options.message,
	}
	// 3) now actually send the email
	try {
		return await transporter.sendMail(mailOptions)
	} catch (error) {
		console.error("Email send failed:", error)
		// We don't want to crash the whole server if an email fails to send (e.g. during seeding or if credentials expire)
		return null
	}
}

module.exports = sendEmail
