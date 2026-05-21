package probe;

import java.io.StringReader;
import java.util.List;
import java.util.Map;

import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVParser;
import org.apache.commons.csv.CSVRecord;

public class Probe {
    enum Header {
        X;

        @Override
        public String toString() {
            return "Y";
        }
    }

    public static void main(String[] args) throws Exception {
        String csv = "X,Y\nleft,right\n";
        CSVFormat format = CSVFormat.DEFAULT.withFirstRecordAsHeader();
        try (CSVParser parser = new CSVParser(new StringReader(csv), format)) {
            List<CSVRecord> records = parser.getRecords();
            CSVRecord record = records.get(0);
            Map<String, Integer> headers = parser.getHeaderMap();
            String viaEnum = record.get(Header.X);
            String viaName = record.get("X");
            String viaToString = record.get("Y");

            System.out.println("{"
                    + "\"enumName\":\"" + Header.X.name() + "\","
                    + "\"enumToString\":\"" + Header.X.toString() + "\","
                    + "\"headerXIndex\":" + headers.get("X") + ","
                    + "\"headerYIndex\":" + headers.get("Y") + ","
                    + "\"viaEnum\":\"" + viaEnum + "\","
                    + "\"viaName\":\"" + viaName + "\","
                    + "\"viaToString\":\"" + viaToString + "\""
                    + "}");
        }
    }
}
