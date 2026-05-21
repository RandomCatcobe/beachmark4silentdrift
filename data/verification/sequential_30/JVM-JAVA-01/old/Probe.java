import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.dataformat.xml.XmlMapper;

public class Probe {
    public static void main(String[] args) throws Exception {
        XmlMapper mapper = new XmlMapper();
        JsonNode node = mapper.readTree("<root><empty/></root>");
        JsonNode empty = node.get("empty");
        System.out.println(empty == null ? "<missing>" : empty.getNodeType() + ":" + empty.toString());
    }
}
