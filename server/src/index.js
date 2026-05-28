import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import mongoose from "mongoose";

dotenv.config();

const app = express();
const port = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

const scholarshipSchema = new mongoose.Schema({
  title: String,
  provider: String,
  amount: Number,
  deadline: String,
  eligibility: String,
  status: { type: String, default: "open" }
}, { timestamps: true });

const applicationSchema = new mongoose.Schema({
  studentId: String,
  scholarshipId: String,
  documents: [String],
  status: { type: String, default: "submitted" },
  score: Number
}, { timestamps: true });

const Scholarship = mongoose.models.Scholarship || mongoose.model("Scholarship", scholarshipSchema);
const Application = mongoose.models.Application || mongoose.model("Application", applicationSchema);

app.get("/api/health", (_req, res) => {
  res.json({ ok: true, service: "AKSHARA BIET Scholarship API" });
});

app.get("/api/scholarships", async (_req, res) => {
  const fallback = [
    { title: "AKSHARA Prime Merit Scholarship", amount: 75000, deadline: "31 Aug 2026", status: "open" },
    { title: "Women in Engineering Grant", amount: 60000, deadline: "15 Sep 2026", status: "open" }
  ];
  if (mongoose.connection.readyState !== 1) return res.json(fallback);
  res.json(await Scholarship.find().sort({ createdAt: -1 }));
});

app.post("/api/scholarships", async (req, res) => {
  if (mongoose.connection.readyState !== 1) return res.status(503).json({ error: "MongoDB is not connected" });
  res.status(201).json(await Scholarship.create(req.body));
});

app.get("/api/applications", async (_req, res) => {
  if (mongoose.connection.readyState !== 1) return res.json([]);
  res.json(await Application.find().sort({ createdAt: -1 }));
});

app.post("/api/applications", async (req, res) => {
  if (mongoose.connection.readyState !== 1) return res.status(503).json({ error: "MongoDB is not connected" });
  res.status(201).json(await Application.create(req.body));
});

async function start() {
  if (process.env.MONGODB_URI) {
    await mongoose.connect(process.env.MONGODB_URI);
    console.log("MongoDB connected");
  } else {
    console.log("MONGODB_URI missing, API running with fallback demo data");
  }
  app.listen(port, () => console.log(`AKSHARA API running on ${port}`));
}

start().catch((error) => {
  console.error(error);
  process.exit(1);
});
