import express from 'express';
import { exec } from 'child_process';
import bodyParser from 'body-parser';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
app.use(bodyParser.json());

app.post('/process-text', (req, res) => {
    const { text, useSentimentAnalysis, ttsProvider } = req.body;
    const command = `python3 tts_sentiment.py "${text}" ${useSentimentAnalysis} ${ttsProvider}`;
    
    exec(command, (error, stdout, stderr) => {
        if (error) {
            console.error(`exec error: ${error}`);
            res.status(500).send(error.message);
            return;
        }
        console.log(`stdout: ${stdout}`);
        console.error(`stderr: ${stderr}`);
        res.send(stdout);
    });
});

app.listen(3000, () => {
    console.log('Server is running on port 3000');
});
