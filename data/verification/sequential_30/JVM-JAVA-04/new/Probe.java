import org.springframework.boot.autoconfigure.web.servlet.WebMvcProperties;

public class Probe {
    public static void main(String[] args) {
        WebMvcProperties properties = new WebMvcProperties();
        System.out.println(properties.getPathmatch().getMatchingStrategy());
    }
}
