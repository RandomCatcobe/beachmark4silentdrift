import org.hibernate.Session;
import org.hibernate.SessionFactory;
import org.hibernate.cfg.Configuration;

public class Probe {
    public static void main(String[] args) {
        Configuration cfg = new Configuration();
        cfg.setProperty("hibernate.connection.driver_class", "org.h2.Driver");
        cfg.setProperty("hibernate.connection.url", "jdbc:h2:mem:drift;DB_CLOSE_DELAY=-1");
        cfg.setProperty("hibernate.dialect", "org.hibernate.dialect.H2Dialect");
        cfg.setProperty("hibernate.show_sql", "false");
        try (SessionFactory sf = cfg.buildSessionFactory(); Session session = sf.openSession()) {
            Object value = session.createNativeQuery("select count(*) from information_schema.tables").getSingleResult();
            System.out.println(value.getClass().getName() + ":" + value);
        }
    }
}
